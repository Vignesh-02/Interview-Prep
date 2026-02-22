# 28. DynamoDB Performance & Best Practices — Senior

## Q1. (Beginner) What is provisioned vs on-demand capacity mode in DynamoDB?

**Answer:**  
**Provisioned**: you set **RCU** (read capacity units) and **WCU** (write capacity units) per table (and per GSI). You pay for provisioned capacity; can use auto scaling. **On-demand**: pay per request; no capacity planning; good for variable or unknown workload. Choose provisioned for predictable load and cost; on-demand for spiky or new workloads.

---

## Q2. (Beginner) What causes throttling in DynamoDB? How does the backend handle it?

**Answer:**  
**Throttling** happens when read or write **exceeds** provisioned capacity (or burst limits in on-demand). DynamoDB returns **ProvisionedThroughputExceededException** (or ThrottlingException). **Backend**: (1) **Retry with exponential backoff** (SDK can do this automatically). (2) Use **jitter** to avoid thundering herd. (3) Increase capacity (provisioned) or spread load (e.g. avoid hot partition). (4) Consider **adaptive capacity** (DynamoDB auto-adjusts per partition).

---

## Q3. (Intermediate) What is a hot partition in DynamoDB? How does adaptive capacity help?

**Answer:**  
**Hot partition**: one partition key gets more traffic than others; that partition has a fraction of total RCU/WCU, so it can throttle. **Adaptive capacity**: DynamoDB can **increase** capacity for a hot partition (within limits) so it absorbs more traffic. It doesn’t remove the need for good key design; design for **high cardinality** and **even distribution** to avoid hot partitions.

---

## Q4. (Intermediate) How do you do a conditional update (e.g. “increment only if current value &lt; 10”) in DynamoDB? Show UpdateItem with condition.

**Answer:**  
Use **ConditionExpression** and **UpdateExpression**:

```javascript
await client.send(new UpdateCommand({
  TableName: 'Counters',
  Key: { pk: 'views', sk: 'page1' },
  UpdateExpression: 'SET #v = if_not_exists(#v, :zero) + :one',
  ConditionExpression: '#v < :max',
  ExpressionAttributeNames: { '#v': 'value' },
  ExpressionAttributeValues: { ':one': 1, ':zero': 0, ':max': 10 }
}));
```
If condition fails, you get ConditionalCheckFailedException. Use **attribute_not_exists**, **=&lt;** etc. for other conditions.

---

## Q5. (Intermediate) What is BatchGetItem and BatchWriteItem? What are the limits and how does the backend use them?

**Answer:**  
**BatchGetItem**: get up to 100 items (across tables) in one call; **BatchWriteItem**: put/delete up to 25 items per call. **Limits**: 100 items per BatchGetItem; 25 put/delete per BatchWriteItem; 16 MB response. **Backend**: batch by 100 (get) or 25 (write); loop with UnprocessedKeys/UnprocessedItems and retry. Use to reduce round-trips (e.g. load many users by ID).

---

## Q6. (Advanced) Production scenario: You have a high-traffic counter (e.g. view count per video). How do you avoid hot partition and throttling while keeping consistency?

**Answer:**  
**Write sharding**: store multiple physical items per logical counter (e.g. pk = VIDEO#id#0 … VIDEO#id#9, sk = COUNT). On increment: **randomly** pick one of the 10 (or N) items and UpdateItem with ADD. On read: **BatchGetItem** all N items and sum. Spreads writes across N partitions; read cost is N reads (or one item if you use a single item and accept some hot partition with adaptive capacity). Alternative: **reserved capacity** for that key or use a separate “hot key” table with more capacity.

---

## Q7. (Advanced) What is DynamoDB Streams? How would the backend use it for event-driven processing?

**Answer:**  
**DynamoDB Streams** is a change log of item-level changes (insert, update, delete). **Backend**: enable stream on the table; **Lambda** (or worker) is triggered by stream records; process changes (e.g. update search index, send notification, replicate). Use **event source mapping** (Lambda) or **Kinesis Client Library** for batching and checkpointing. Use for: search sync, cache invalidation, audit, async workflows.

---

## Q8. (Advanced) How do you implement pagination for the API when using Query? What do you return to the client?

**Answer:**  
**Query** returns **LastEvaluatedKey** when there are more results. **Backend**: pass **ExclusiveStartKey** from the previous response (or from client token) and **Limit** (page size). Return to client: **items** plus a **nextToken** (e.g. base64-encoded LastEvaluatedKey). Client sends nextToken as startKey for the next page. Don’t expose raw keys; encode and validate token size.

---

## Q9. (Advanced) What is the best way to do “query by non-key attribute” (e.g. by email) in DynamoDB without Scan?

**Answer:**  
**GSI** with that attribute as **partition key** (e.g. GSI_PK = email). Query the GSI; get one or more items. If email is unique, you get one item (e.g. userId). Then GetItem on base table by userId if needed. **No Scan** for this pattern; always use GSI (or LSI if the attribute is a different sort key for the same partition). Design the GSI at table creation or add later.

---

## Q10. (Advanced) Compare DynamoDB’s conditional writes and transactions to Cassandra’s lightweight transactions (LWT). When would you use DynamoDB transactions?

**Answer:**  
**DynamoDB**: **Conditional writes** (ConditionExpression) for single-item conditions (e.g. put if not exists). **Transactions** (TransactWriteItems) for multi-item atomic write (up to 100 items). **Cassandra LWT**: conditional insert/update using IF (e.g. IF version = x); linearizable but more expensive. **DynamoDB transactions**: use when you need **multiple items** updated atomically (e.g. debit one account, credit another). Use conditional writes for single-item optimistic locking; use transactions for cross-item consistency.
