# 19. DynamoDB Basics & Data Model

## Q1. (Beginner) What is Amazon DynamoDB? What type of database is it?

**Answer:**  
**DynamoDB** is AWS’s managed **NoSQL** key-value and document database. It provides **partition key** (required) and optional **sort key**; single-digit millisecond latency at scale; serverless (pay per request/capacity). Data is stored as **items** (rows) with **attributes** (columns); schema is flexible per item.

---

## Q2. (Beginner) What is a partition key (PK) and sort key (SK)? What is a composite primary key?

**Answer:**  
**Partition key**: determines which partition (and thus which physical storage) the item lives in; must be unique if there’s no sort key. **Sort key**: optional; (PK, SK) together must be unique. With sort key, you can have multiple items per partition key, ordered by sort key. **Composite primary key** = (partition key, sort key). Query can be by PK only (all items in partition) or by PK + condition on SK (e.g. range).

---

## Q3. (Intermediate) How do you get an item by primary key in DynamoDB? Show AWS SDK (JavaScript) call.

**Answer:**
```javascript
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand } = require('@aws-sdk/lib-dynamodb');

const client = DynamoDBDocumentClient.from(new DynamoDBClient({ region: 'us-east-1' }));

const result = await client.send(new GetCommand({
  TableName: 'Users',
  Key: { userId: 'u123', sk: 'PROFILE' }  // or just { userId: 'u123' } if no sort key
}));
const item = result.Item;  // undefined if not found
```

---

## Q4. (Intermediate) What is the difference between GetItem and Query? When would you use each?

**Answer:**  
**GetItem**: fetch **one** item by full primary key (PK, and SK if present). **Query**: fetch **all** items with a given partition key (and optional condition on sort key). Use GetItem for “get this exact item”; use Query for “get all items for this partition” or “items in this partition where SK between X and Y.”

---

## Q5. (Intermediate) How do you write an item (put) and update specific attributes? What is UpdateItem?

**Answer:**  
**PutItem**: overwrites the entire item; use when you’re replacing the item. **UpdateItem**: update only specified attributes (with SET, REMOVE, ADD); item is created if it doesn’t exist (upsert). Use UpdateItem for partial updates (e.g. set `lastLogin = now`) and for **atomic counters** (ADD). **DeleteItem**: delete by primary key.

---

## Q6. (Advanced) What is strong consistency vs eventual consistency for reads? How do you request each in the SDK?

**Answer:**  
**Strong consistency**: read returns the latest committed write. **Eventual**: read may return slightly stale data; lower cost and latency. **SDK**: in GetItem, Query, Scan, set **ConsistentRead: true** for strong. Default is eventually consistent. Use strong when you need read-your-writes (e.g. after update); use eventual for throughput and cost when staleness is acceptable.

---

## Q7. (Advanced) How do you do a conditional write (e.g. put only if item does not exist)? What is a condition expression?

**Answer:**  
Use **ConditionExpression** on PutItem, UpdateItem, or DeleteItem. **Put only if not exists**: `ConditionExpression: 'attribute_not_exists(userId)'`. **Update only if version matches**: `ConditionExpression: '#v = :expected', ExpressionAttributeNames: { '#v': 'version' }, ExpressionAttributeValues: { ':expected': 5 }`. If condition fails, the write returns ConditionalCheckFailedException; app can retry or handle.

---

## Q8. (Advanced) Production scenario: Your API creates a user. You want to ensure no duplicate email. Table has PK=userId, and you need uniqueness on email. How do you enforce it with DynamoDB?

**Answer:**  
**Option 1**: **GSI** on email (email as PK); make it a **unique** key. On user create: (1) PutItem into main table (userId as PK). (2) PutItem into GSI or a second table keyed by email — use **ConditionExpression: 'attribute_not_exists(email)'** so duplicate email fails. **Option 2**: Separate “email → userId” table: PutItem with PK=email, ConditionExpression attribute_not_exists(email); then write user in main table. Either way, use a single table or GSI keyed by email and conditional write to enforce uniqueness; handle ConditionalCheckFailedException as “email taken.”

---

## Q9. (Advanced) What is Scan? Why is it expensive and when should you avoid it?

**Answer:**  
**Scan** reads **every** item in the table (or a filter is applied after read). It consumes read capacity for the entire scan; slow and costly for large tables. **Avoid** for regular API paths. Use **Query** (by partition key) or **GetItem** instead. Use Scan only for export, analytics, or one-off admin; consider parallel scan and limit if you must.

---

## Q10. (Advanced) How does the Node.js backend handle pagination for Query and Scan? What are LastEvaluatedKey and ExclusiveStartKey?

**Answer:**  
DynamoDB returns **LastEvaluatedKey** when there are more results. Pass it as **ExclusiveStartKey** in the next request to get the next page. **Example:**
```javascript
let lastKey;
const items = [];
do {
  const result = await client.send(new QueryCommand({
    TableName: 'MyTable',
    KeyConditionExpression: 'pk = :pk',
    ExpressionAttributeValues: { ':pk': 'user#123' },
    ExclusiveStartKey: lastKey,
    Limit: 100
  }));
  items.push(...result.Items);
  lastKey = result.LastEvaluatedKey;
} while (lastKey);
```
Return a pagination token to the client (e.g. base64 of LastEvaluatedKey) so they can request the next page.
