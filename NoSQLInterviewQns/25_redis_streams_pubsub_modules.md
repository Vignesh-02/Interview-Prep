# 25. Redis Streams, Pub/Sub & Modules — Senior

## Q1. (Beginner) What is Redis Pub/Sub? What are its limitations compared to a message queue?

**Answer:**  
**Pub/Sub**: publishers send messages to **channels**; subscribers receive in real time. **Limitations**: (1) **No persistence** — if no subscriber is connected, message is lost. (2) **No acknowledgment** — no “at least once” delivery. (3) **Fire-and-forget** — no replay. (4) **No consumer groups** — every subscriber gets every message (broadcast). For durable, acknowledged, replayable messaging use **Redis Streams** or a dedicated queue (e.g. RabbitMQ, SQS).

---

## Q2. (Beginner) What is a Redis Stream? How is it different from a List?

**Answer:**  
A **Stream** is an append-only log of **entries**; each entry has an ID (timestamp-sequence) and field-value pairs. **Consumers** read by ID range or by consumer group. **Difference from List**: Streams support **consumer groups** (competing consumers, ack, pending list), **range queries by ID**, and **persistence**. Lists are simpler (LPUSH/RPOP); Streams are for durable, multi-consumer messaging.

---

## Q3. (Intermediate) How do you add to a stream and read from it (XADD, XREAD)? Show basic usage.

**Answer:**  
**XADD**: `XADD mystream * field1 value1 field2 value2` — * = auto ID; returns ID. **XREAD**: `XREAD COUNT 10 STREAMS mystream 0` — read from start (0); use last ID for next read. **Blocking**: `XREAD BLOCK 5000 STREAMS mystream $` — wait 5s for new entries ($ = latest). In Node (ioredis): `redis.xadd('mystream', '*', 'event', 'data')`; `redis.xread('STREAMS', 'mystream', '0')`.

---

## Q4. (Intermediate) What are consumer groups? What is XREADGROUP?

**Answer:**  
**Consumer groups**: multiple consumers share the stream; each message is delivered to **one** consumer in the group. **XREADGROUP GROUP mygroup myconsumer STREAMS mystream &gt;** — &gt; means “new messages for me.” Messages are tracked as **pending** until **XACK**. If a consumer dies, others can claim pending messages (XPENDING, XCLAIM). Use for **competing consumers** and at-least-once processing.

---

## Q5. (Intermediate) How do you acknowledge a message in a stream (XACK)? Why is it important?

**Answer:**  
**XACK stream group id [id ...]** marks message(s) as processed. Until acked, the message stays in the **pending list** and can be claimed by another consumer (e.g. on timeout). So XACK is required for “at least once” — process message, then XACK; if you don’t ack, the same message may be redelivered. After XACK, the message is no longer delivered to the group.

---

## Q6. (Advanced) Production scenario: You need a simple task queue: producers add jobs to a stream, workers process and ack. Implement with Redis Streams and Node.js (one producer, one consumer group, one worker).

**Answer:**
```javascript
// Producer
async function addJob(redis, stream, job) {
  return redis.xadd(stream, '*', 'data', JSON.stringify(job));
}

// Worker (consumer group: create once with XGROUP CREATE)
async function runWorker(redis, stream, group, consumer, handler) {
  await redis.xgroup('CREATE', stream, group, '0', 'MKSTREAM').catch(() => {});
  while (true) {
    const [, messages] = await redis.xreadgroup('GROUP', group, consumer, 'BLOCK', 5000, 'STREAMS', stream, '>');
    if (!messages || !messages.length) continue;
    for (const [streamName, list] of messages) {
      for (const [id, fields] of list) {
        const data = JSON.parse(fields[1]);
        try {
          await handler(data);
          await redis.xack(stream, group, id);
        } catch (e) {
          // leave unacked for retry or XCLAIM
        }
      }
    }
  }
}
```

---

## Q7. (Advanced) What are Redis Modules? Name two (e.g. RediSearch, RedisJSON) and one use case each.

**Answer:**  
**RediSearch**: full-text search and secondary indexes on hashes; use for search inside Redis (e.g. product search, tag search) without Elasticsearch. **RedisJSON**: JSON document type with path queries; use for document-like storage and partial updates. **RedisBloom**: Bloom filter, Cuckoo filter; use for “might exist” checks and deduplication. **RedisGraph**: graph; use for relationship queries. Modules extend Redis for specific workloads.

---

## Q8. (Advanced) When would you choose Redis Streams over Kafka or SQS for a backend?

**Answer:**  
**Redis Streams** when: (1) Already using Redis; (2) Moderate volume and retention; (3) Need low latency and simple ops; (4) Single Redis (or Cluster) is enough. **Kafka** when: (1) Very high throughput and retention; (2) Multiple consumers and replay; (3) Ecosystem (Kafka Connect, etc.). **SQS** when: (1) Managed, no ops; (2) AWS-native; (3) Decoupling and at-least-once. Choose Redis Streams for in-app or same-datacenter task queues and event log when scale fits Redis.

---

## Q9. (Advanced) How do you handle “pending” messages that were not acked (e.g. consumer crashed)? What are XPENDING and XCLAIM?

**Answer:**  
**XPENDING stream group** (or with range) shows pending message IDs and which consumer has them. **XCLAIM stream group consumer min-idle-time id [id ...]** claims pending messages that have been idle longer than min-idle-time (e.g. consumer died). Another consumer or a recovery job can XCLAIM and reprocess, then XACK. Use **XCLAIM** to implement “timeout and reassign” for at-least-once processing.

---

## Q10. (Advanced) How would you use Redis Pub/Sub from the backend to invalidate in-process caches across multiple API instances when data changes?

**Answer:**  
(1) **Subscribe** to a channel (e.g. `cache:invalidate`) in each API instance (dedicated connection or shared). (2) On **data change** (e.g. DB update), **publish** to that channel with key or pattern (e.g. `user:123` or `user:*`). (3) Each instance’s subscriber **receives** and removes the key (or matching keys) from its **local** cache. (4) Next request in that instance does cache-aside and loads fresh from DB/Redis. Use one channel per “namespace” or encode key in message; keep messages small (key names or patterns).
