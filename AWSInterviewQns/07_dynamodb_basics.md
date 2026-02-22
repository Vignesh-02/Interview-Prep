# 7. DynamoDB Basics

## Q1. (Beginner) What is DynamoDB? How does it differ from RDS?

**Answer:**  
**DynamoDB** is a managed **NoSQL** key-value and document database; **serverless** (pay per request or provisioned capacity). **vs RDS**: no SQL; **partition key** (required) + optional **sort key**; single-digit ms latency; scales horizontally. Use DynamoDB for key-value access, high scale, variable schema; use RDS for relational queries, transactions, reporting.

---

## Q2. (Beginner) What is a partition key and sort key? What is the primary key?

**Answer:**  
**Partition key** (PK): determines which partition (and node) the item lives in; must be unique if there’s no sort key. **Sort key** (SK): optional; (PK, SK) together must be unique; enables **range queries** within a partition. **Primary key** = PK or (PK, SK). Design for access patterns: e.g. PK = userId, SK = orderId for “get all orders for user.”

---

## Q3. (Intermediate) How do you read an item by primary key from DynamoDB in code? Show SDK (Node.js or Python).

**Answer (Node.js):**
```javascript
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand } = require('@aws-sdk/lib-dynamodb');
const client = DynamoDBDocumentClient.from(new DynamoDBClient({ region: 'us-east-1' }));
const r = await client.send(new GetCommand({
  TableName: 'Users',
  Key: { userId: 'u1', sk: 'PROFILE' }
}));
const item = r.Item;
```

**Answer (Python):**
```python
import boto3
from boto3.dynamodb.conditions import Key
ddb = boto3.resource('dynamodb')
table = ddb.Table('Users')
r = table.get_item(Key={'userId': 'u1', 'sk': 'PROFILE'})
item = r.get('Item')
```

---

## Q4. (Intermediate) What is the difference between GetItem and Query? When would you use BatchGetItem?

**Answer:**  
**GetItem**: fetch **one** item by full primary key. **Query**: fetch **all** items with same partition key (and optional condition on sort key). **BatchGetItem**: get up to **100** items (across tables) in one call; items can have different partition keys. Use BatchGetItem to reduce round-trips when loading many items by key (e.g. 50 users by userId).

---

## Q5. (Intermediate) What is provisioned vs on-demand capacity? When would you choose each?

**Answer:**  
**Provisioned**: you set **RCU** (read) and **WCU** (write) per table; pay for capacity; can use auto scaling. **On-demand**: pay per request; no capacity planning; good for variable or unknown workload. **Choose provisioned** for predictable, steady load (often cheaper). **Choose on-demand** for spiky, new, or hard-to-predict traffic.

---

## Q6. (Advanced) Production scenario: Your app stores user sessions in DynamoDB (PK = sessionId). Traffic is 10k requests/min; each request does one GetItem. How do you size capacity and avoid throttling?

**Answer:**  
**On-demand**: no sizing; DynamoDB scales; pay per request; good for variable 10k/min. **Provisioned**: 10k reads/min ≈ 167 RCU (1 read/sec ≈ 1 RCU for eventually consistent). Set **auto scaling** with target utilization (e.g. 70%); min/max RCU to handle spikes. **Best**: start **on-demand** to avoid throttling; switch to **provisioned** with auto scaling when pattern is predictable to optimize cost. Use **consistent read** only when needed (2× RCU).

---

## Q7. (Advanced) What is a GSI? How do you use it to “query by email” when the base table is keyed by userId?

**Answer:**  
**GSI** (Global Secondary Index): alternate **partition key** (and optional sort key); DynamoDB maintains it. Create GSI with **email** as partition key. **Query** the GSI with `email = 'x@y.com'` to get item(s); you get userId from the item, then can GetItem on base table if needed. GSI has its own capacity (provisioned or on-demand). Use for access patterns that don’t use the base table key.

---

## Q8. (Advanced) Production scenario: You need to implement “get last 10 orders for user” and “get order by ID.” Design the table and one GSI if needed. Show key design.

**Answer:**  
**Base table**: PK = `USER#userId`, SK = `ORDER#orderId` (or `ORDER#timestamp#orderId` for chronological order). **Get last 10 orders**: Query base table PK = USER#u1, ScanIndexForward = false, Limit 10. **Get order by ID**: need userId — if client has it, GetItem(PK=USER#userId, SK=ORDER#orderId). If you only have orderId, **GSI**: GSI_PK = orderId (if unique), GSI_SK = userId; Query GSI by orderId to get userId, then GetItem. Or store orders in a second table/GSI keyed by orderId with userId as attribute.

---

## Q9. (Advanced) Compare DynamoDB for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: single table or few tables; on-demand or low provisioned; IAM role for app; backup (PITR) optional. **Enterprise**: **single-table design** or disciplined multi-table; **GSIs** for access patterns; **DAX** for read-heavy hot keys; **global tables** for multi-region; **backup** and retention; **encryption** (KMS); **fine-grained IAM**; monitoring and alarms on throttling.

---

## Q10. (Advanced) Senior red flags to avoid with DynamoDB

**Answer:**  
- **Scan** for regular API paths (use Query/GetItem).  
- **Hot partition** — one partition key gets most traffic (design for high cardinality).  
- **No GSI** for “query by X” and using Scan.  
- **Overuse of consistent read** (2× cost) when eventual is fine.  
- **No retry/backoff** for throttling (use SDK default or exponential backoff).  
- **Large items** (> 400 KB) affecting throughput and cost.  
- **No backup** or point-in-time recovery for production.

---

**Tradeoffs:** Startup: on-demand, simple key design. Medium: provisioned + auto scaling, GSIs. Enterprise: single-table design, DAX, global tables, encryption.
