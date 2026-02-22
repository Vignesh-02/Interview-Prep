# 9. SQS & SNS (Messaging)

## Q1. (Beginner) What is SQS? What is the difference between standard and FIFO queues?

**Answer:**  
**SQS** is a managed **message queue**: producers send messages; consumers poll (or long-poll) and process. **Standard**: best-effort ordering; at-least-once delivery; high throughput; possible duplicates. **FIFO**: strict order per **message group**; exactly-once processing (with dedup); 300 msg/s without batching. Use Standard for throughput; FIFO when order and dedup matter.

---

## Q2. (Beginner) What is SNS? How does it differ from SQS?

**Answer:**  
**SNS** is **pub/sub**: publishers send to a **topic**; **subscribers** (SQS, Lambda, HTTP, email) receive. **One-to-many**. **SQS** is **queue**: one or more consumers pull messages; **one-to-one** (or competing consumers). Use **SNS** to fan-out (one event → many subscribers); use **SQS** for decoupling and buffering (producer → queue → consumer).

---

## Q3. (Intermediate) How do you connect SNS to SQS so that every message published to the topic is delivered to the queue? Why use this pattern?

**Answer:**  
**Subscribe** the SQS queue to the SNS topic (SNS subscription with protocol SQS, endpoint = queue ARN). SNS pushes to the queue. **Permission**: SNS needs permission to send to the queue (resource policy on the queue). **Pattern**: decouple publisher from consumers; buffer in SQS; retry and DLQ; multiple queues can subscribe to same topic (fan-out). Use for event-driven architecture (e.g. order created → inventory, email, analytics queues).

---

## Q4. (Intermediate) What is a Dead Letter Queue (DLQ)? When would you use it with Lambda and SQS?

**Answer:**  
**DLQ** is a queue where **failed** messages are sent after max receives (or Lambda failures). **With Lambda + SQS**: configure the source queue’s **redrive policy** (maxReceiveCount = 3, deadLetterTarget = DLQ ARN). After 3 failed processings, message goes to DLQ. **Use**: avoid losing messages; inspect and replay or alert. Always use a DLQ for production queues and alarm on DLQ depth.

---

## Q5. (Intermediate) Write backend code (Node.js or Python) to send a message to SQS and then receive (and delete) one message.

**Answer (Node.js):**
```javascript
const { SQSClient, SendMessageCommand, ReceiveMessageCommand, DeleteMessageCommand } = require('@aws-sdk/client-sqs');
const client = new SQSClient({ region: 'us-east-1' });
const queueUrl = 'https://sqs.us-east-1.amazonaws.com/123456789/my-queue';
await client.send(new SendMessageCommand({ QueueUrl: queueUrl, MessageBody: JSON.stringify({ id: 1, data: 'hello' }) }));
const recv = await client.send(new ReceiveMessageCommand({ QueueUrl: queueUrl, MaxNumberOfMessages: 1, WaitTimeSeconds: 5 }));
const msg = recv.Messages?.[0];
if (msg) {
  await client.send(new DeleteMessageCommand({ QueueUrl: queueUrl, ReceiptHandle: msg.ReceiptHandle }));
}
```

---

## Q6. (Advanced) Production scenario: Order service publishes “OrderCreated” to SNS. Inventory and Email services must consume. Inventory must not be overwhelmed (max 10 msg/s). Design the flow with SNS, SQS, and Lambda.

**Answer:**  
(1) **SNS topic** “OrderCreated”. (2) **Two SQS queues**: “inventory-queue” (subscribed to SNS), “email-queue” (subscribed to SNS). (3) **Inventory**: Lambda triggered by inventory-queue with **reserved concurrency 10** (or set queue visibility and batch size so effective rate ≈ 10/s). (4) **Email**: Lambda triggered by email-queue (no strict rate). (5) **DLQ** for each queue; alarm on DLQ depth. (6) Use **batch size** and **visibility timeout** so Lambda doesn’t timeout before processing. **Result**: fan-out from SNS; SQS buffers and rate-limits inventory; email can scale independently.

---

## Q7. (Advanced) What is visibility timeout? What happens if your Lambda processes longer than the visibility timeout?

**Answer:**  
**Visibility timeout**: after a consumer receives a message, it’s **invisible** to other consumers for this period; after that it becomes visible again (for redelivery). If **Lambda runs longer** than visibility timeout, the message may be **redelivered** to another (or same) consumer while the first is still processing → **duplicate processing**. **Fix**: set visibility timeout **≥** Lambda timeout (e.g. 6× Lambda timeout); or use **extend** visibility in long-running processing (e.g. with SQS API). Design for **idempotency** in case of duplicates.

---

## Q8. (Advanced) Production scenario: You use SQS standard queue. Some messages are processed twice; some are delivered out of order. How do you make the system correct and when would you switch to FIFO?

**Answer:**  
**At-least-once + order**: (1) **Idempotency** — consumer checks “already processed?” (e.g. DynamoDB keyed by message dedup ID) before doing work; skip or return success if yes. (2) **Order**: if strict order per entity (e.g. per user), use **FIFO** with **message group ID** = userId so all messages for that user are ordered. **Switch to FIFO** when you need ordering per group and exactly-once semantics; accept lower throughput or use multiple message groups to parallelize.

---

## Q9. (Advanced) Compare SQS/SNS for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: one or few queues; Standard queue; SNS for fan-out; DLQ and basic alarm. **Medium**: FIFO where order matters; dead-letter and retry policy; SNS filtering; metrics and alarms. **Enterprise**: **encryption** (KMS); **cross-account** access via resource policies; **FIFO** and dedup; **large message** via S3 (reference in message); compliance and audit (CloudTrail).

---

## Q10. (Advanced) Senior red flags to avoid with SQS/SNS

**Answer:**  
- **No DLQ** for production queues.  
- **Visibility timeout** shorter than processing time (duplicates).  
- **No idempotency** in consumers (duplicate messages cause double side effects).  
- **Polling** without long polling (WaitTimeSeconds = 20) — wastes requests.  
- **SNS** with no retry or DLQ for HTTP/Lambda subscribers.  
- **Sensitive data** in message body (encrypt or use S3 reference).  
- **Ignoring** queue depth and age metrics (backlog growth).

---

**Tradeoffs:** Startup: Standard queue, SNS, one DLQ. Medium: FIFO where needed, concurrency limits, alarms. Enterprise: encryption, cross-account, compliance.
